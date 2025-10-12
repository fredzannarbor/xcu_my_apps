#!/usr/bin/env python3
"""
Prepress script for Not A Miracle Readers imprint.
Processes markdown manuscripts for early chapter books.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Markdown parsing
import markdown
from bs4 import BeautifulSoup


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text."""
    if not text:
        return ""

    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
        '\u2014': '---',  # em dash
        '\u2013': '--',   # en dash
        '\u2019': "'",    # right single quote
        '\u201c': '``',   # left double quote
        '\u201d': "''",   # right double quote
    }

    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)

    return result


def parse_markdown_manuscript(md_path: Path) -> Dict[str, Any]:
    """
    Parse a markdown manuscript into structured data.

    Returns:
        Dictionary with title, subtitle, chapters, and back matter
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into sections
    lines = content.split('\n')

    # Extract title (first # heading)
    title = ""
    subtitle = ""
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line[2:].strip()
            # Check next line for subtitle (bold text)
            if i + 2 < len(lines) and lines[i + 2].startswith('**'):
                subtitle = lines[i + 2].strip('*').strip()
            break

    # Extract chapters
    chapters = []
    current_chapter = None
    chapter_content = []
    in_discussion = False
    discussion_questions = []

    for line in lines:
        # Check for chapter heading
        if line.startswith('## Chapter '):
            # Save previous chapter
            if current_chapter:
                chapters.append({
                    'number': current_chapter,
                    'title': chapter_title,
                    'content': '\n\n'.join(chapter_content).strip()  # Use \n\n for paragraph breaks
                })
                chapter_content = []

            # Start new chapter
            match = re.match(r'## Chapter (\d+): (.+)', line)
            if match:
                current_chapter = match.group(1)
                chapter_title = match.group(2)

        # Check for discussion questions section
        elif line.startswith('**Discussion Questions:**'):
            in_discussion = True
            if current_chapter:
                chapters.append({
                    'number': current_chapter,
                    'title': chapter_title,
                    'content': '\n\n'.join(chapter_content).strip()  # Use \n\n for paragraph breaks
                })
                current_chapter = None
                chapter_content = []

        # Check for "About This Story" section (end of main content)
        elif line.startswith('## About This Story'):
            if current_chapter:
                chapters.append({
                    'number': current_chapter,
                    'title': chapter_title,
                    'content': '\n\n'.join(chapter_content).strip()  # Use \n\n for paragraph breaks
                })
                current_chapter = None
            break

        # Accumulate content - preserve blank lines as paragraph separators
        elif current_chapter and not line.startswith('---'):
            if line.strip():  # Non-empty line
                chapter_content.append(line.strip())
            elif chapter_content and chapter_content[-1] != '':  # Blank line (but avoid consecutive blanks)
                chapter_content.append('')  # Mark paragraph break

    # Save last chapter if exists
    if current_chapter and chapter_content:
        chapters.append({
            'number': current_chapter,
            'title': chapter_title,
            'content': '\n\n'.join([p for p in chapter_content if p]).strip()  # Filter empty strings, join with \n\n
        })

    # Extract discussion questions
    in_discussion = False
    for line in lines:
        if '**Discussion Questions:**' in line:
            in_discussion = True
            continue
        if in_discussion and line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
            # Remove number prefix
            question = re.sub(r'^\d+\.\s*', '', line.strip())
            discussion_questions.append(question)

    return {
        'title': title,
        'subtitle': subtitle,
        'chapters': chapters,
        'discussion_questions': discussion_questions
    }


def create_title_page(data: Dict[str, Any], build_dir: Path) -> None:
    """Generate title page LaTeX file."""
    title = escape_latex(data.get('title', 'Untitled'))
    subtitle = escape_latex(data.get('subtitle', ''))
    author = escape_latex(data.get('author', 'Not A Miracle Team'))

    content = textwrap.dedent(f"""
        % Set the title for headers
        \\renewcommand{{\\thetitle}}{{{title}}}

        \\thispagestyle{{empty}}
        \\vspace*{{2in}}

        \\begin{{center}}
        {{\\Huge\\sffamily\\bfseries {title}}}

        \\vspace{{0.5in}}

        {{\\Large\\sffamily {subtitle}}}

        \\vspace{{1in}}

        {{\\large\\sffamily by {author}}}
        \\end{{center}}

        \\clearpage
    """)

    with open(build_dir / 'title_page.tex', 'w', encoding='utf-8') as f:
        f.write(content)


def create_copyright_page(data: Dict[str, Any], build_dir: Path, config: Dict[str, Any]) -> None:
    """Generate copyright page LaTeX file."""
    title = escape_latex(data.get('title', 'Untitled'))
    imprint = escape_latex(config.get('imprint', 'Not A Miracle Readers'))
    publisher = escape_latex(config.get('publisher', 'Nimble Books LLC'))
    isbn = data.get('isbn', '000-0-00000-000-0')

    content = textwrap.dedent(f"""
        \\thispagestyle{{empty}}
        \\vspace*{{\\fill}}

        \\begin{{center}}
        {{\\small
        Copyright \\textcopyright\\ 2025 by {publisher}

        All rights reserved.

        Published by {imprint}

        ISBN: {isbn}

        \\vspace{{0.3in}}

        No part of this book may be reproduced in any form\\\\
        without permission in writing from the publisher.

        \\vspace{{0.3in}}

        www.nimblebooks.com
        }}
        \\end{{center}}

        \\vspace*{{\\fill}}
        \\clearpage
    """)

    with open(build_dir / 'copyright_page.tex', 'w', encoding='utf-8') as f:
        f.write(content)


def create_table_of_contents(data: Dict[str, Any], build_dir: Path) -> None:
    """Generate table of contents LaTeX file."""
    content = textwrap.dedent("""
        \\tableofcontents
        \\clearpage
    """)

    with open(build_dir / 'table_of_contents.tex', 'w', encoding='utf-8') as f:
        f.write(content)


def create_chapters_file(data: Dict[str, Any], build_dir: Path) -> None:
    """Generate chapters LaTeX file with all chapter content."""
    chapters = data.get('chapters', [])

    content_parts = []

    for chapter in chapters:
        chapter_num = chapter.get('number', '1')
        chapter_title = escape_latex(chapter.get('title', 'Untitled'))
        chapter_text = chapter.get('content', '')

        # Start chapter
        content_parts.append(f"\\chapter{{{chapter_title}}}")
        content_parts.append("")

        # Process chapter content - split into paragraphs
        # First normalize line breaks: single \n stays, double \n\n becomes paragraph break
        paragraphs = [p.strip() for p in chapter_text.split('\n\n') if p.strip()]

        for para in paragraphs:
            # Remove internal single line breaks (they shouldn't break paragraphs)
            para = para.replace('\n', ' ')

            # Remove markdown formatting (bold/italic asterisks and underscores)
            para_clean = para.replace('**', '').replace('*', '').replace('__', '').replace('_', '')

            # Escape LaTeX special characters
            para_escaped = escape_latex(para_clean)

            # Handle dialogue (quoted text) - convert to proper LaTeX quotes
            para_escaped = re.sub(r'"([^"]+)"', r"``\1''", para_escaped)

            content_parts.append(para_escaped)
            content_parts.append("")  # Add blank line between paragraphs in LaTeX

        # Add page break after chapter (except last one)
        content_parts.append("\\clearpage")
        content_parts.append("")

    with open(build_dir / 'chapters.tex', 'w', encoding='utf-8') as f:
        f.write('\n'.join(content_parts))


def create_discussion_questions(data: Dict[str, Any], build_dir: Path) -> None:
    """Generate discussion questions LaTeX file."""
    questions = data.get('discussion_questions', [])

    if not questions:
        return

    content_parts = [
        "\\chapter*{Discussion Questions}",
        "\\addcontentsline{toc}{chapter}{Discussion Questions}",
        "",
        "\\begin{enumerate}[leftmargin=*, itemsep=0.3in]"
    ]

    for question in questions:
        q_escaped = escape_latex(question)
        content_parts.append(f"\\item {q_escaped}")

    content_parts.append("\\end{enumerate}")

    with open(build_dir / 'discussion_questions.tex', 'w', encoding='utf-8') as f:
        f.write('\n'.join(content_parts))


def compile_latex(build_dir: Path, template_path: Path, output_name: str) -> Path:
    """
    Compile LaTeX files to PDF using LuaLaTeX.

    Args:
        build_dir: Directory containing .tex files
        template_path: Path to the main template.tex file
        output_name: Base name for output PDF

    Returns:
        Path to generated PDF
    """
    # Copy template to build directory as main.tex
    shutil.copy(template_path, build_dir / 'main.tex')

    # Run LuaLaTeX twice (for TOC)
    for i in range(2):
        result = subprocess.run(
            ['lualatex', '-interaction=nonstopmode', 'main.tex'],
            cwd=build_dir,
            capture_output=True,
            text=True
        )

        # Check if PDF was generated (even if there were warnings)
        if i == 1 and not (build_dir / 'main.pdf').exists():
            print(f"LaTeX compilation failed (pass {i+1}):")
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError("LaTeX compilation failed - no PDF generated")

    # Rename output
    pdf_path = build_dir / 'main.pdf'
    final_pdf = build_dir / f'{output_name}.pdf'

    if pdf_path.exists():
        shutil.move(pdf_path, final_pdf)
        return final_pdf
    else:
        raise RuntimeError(f"PDF not generated at {pdf_path}")


def process_markdown_book(
    md_path: Path,
    output_dir: Path,
    config_path: Path,
    isbn: str = None,
    author: str = None
) -> Dict[str, Path]:
    """
    Main processing function for markdown manuscripts.

    Args:
        md_path: Path to markdown manuscript
        output_dir: Directory for final outputs
        config_path: Path to imprint config JSON
        isbn: Optional ISBN to use
        author: Optional author name

    Returns:
        Dictionary with paths to generated files
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Parse markdown
    print(f"Parsing markdown from {md_path}...")
    data = parse_markdown_manuscript(md_path)

    # Add metadata
    if isbn:
        data['isbn'] = isbn
    if author:
        data['author'] = author
    else:
        data['author'] = 'Not A Miracle Team'

    # Create build directory
    build_dir = output_dir / 'build'
    build_dir.mkdir(parents=True, exist_ok=True)

    # Generate LaTeX files
    print("Generating LaTeX files...")
    create_title_page(data, build_dir)
    create_copyright_page(data, build_dir, config)
    create_table_of_contents(data, build_dir)
    create_chapters_file(data, build_dir)
    create_discussion_questions(data, build_dir)

    # Get template path - it's in the same directory as this script
    imprint_dir = Path(__file__).parent
    template_path = imprint_dir / 'template.tex'

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Compile PDF
    print("Compiling PDF with LuaLaTeX...")
    output_name = md_path.stem
    pdf_path = compile_latex(build_dir, template_path, output_name)

    # Copy to final output location
    final_pdf = output_dir / f"{output_name}_interior.pdf"
    shutil.copy(pdf_path, final_pdf)

    print(f"✓ Interior PDF generated: {final_pdf}")

    return {
        'interior_pdf': final_pdf,
        'build_dir': build_dir,
        'data': data
    }


def main():
    parser = argparse.ArgumentParser(
        description='Prepress processing for Not A Miracle Readers early chapter books'
    )
    parser.add_argument(
        'markdown_file',
        type=Path,
        help='Path to markdown manuscript file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory for generated files'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to imprint config JSON (auto-detected if not provided)'
    )
    parser.add_argument(
        '--isbn',
        help='ISBN for the book'
    )
    parser.add_argument(
        '--author',
        help='Author name'
    )

    args = parser.parse_args()

    # Auto-detect config if not provided
    if not args.config:
        # Look for config in standard location
        repo_root = Path(__file__).parent.parent.parent
        args.config = repo_root / 'configs' / 'imprints' / 'not_a_miracle_readers.json'

    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    if not args.markdown_file.exists():
        print(f"Error: Markdown file not found: {args.markdown_file}")
        sys.exit(1)

    # Process the book
    try:
        results = process_markdown_book(
            args.markdown_file,
            args.output_dir,
            args.config,
            isbn=args.isbn,
            author=args.author
        )

        print("\n" + "="*60)
        print("PREPRESS COMPLETE")
        print("="*60)
        print(f"Interior PDF: {results['interior_pdf']}")
        print(f"Build directory: {results['build_dir']}")
        print("\nNext steps:")
        print("1. Review the interior PDF")
        print("2. Generate cover using cover_template.tex")
        print("3. Upload to Lightning Source")

    except Exception as e:
        print(f"\nError during prepress: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
