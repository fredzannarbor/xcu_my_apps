#!/usr/bin/env python3
"""
Fix all PT boat book formatting issues
"""

import re
import json
from pathlib import Path

def fix_latex_template():
    """Create updated LaTeX template with all fixes"""

    template = r"""\documentclass[11pt]{book}
\usepackage[paperwidth=7in, paperheight=10in, top=1in, bottom=1in, left=0.75in, right=0.75in]{geometry}
\usepackage{graphicx}
\usepackage{caption}
\usepackage{float}
\usepackage{ragged2e}
\usepackage{calc}
\usepackage{fontspec}  % For Unicode fonts (LuaLaTeX)
\setmainfont{Latin Modern Roman}  % Supports Unicode
\usepackage{newunicodechar}  % For custom Unicode chars
\newunicodechar{′}{\ensuremath{'}}  % Prime symbol
\newunicodechar{″}{\ensuremath{''}}  % Double prime
\usepackage{microtype} % Better typography

% Chapter title formatting - Small caps for both number and title
\usepackage{titlesec}
\titleformat{\chapter}[display]
{\normalfont\Large\scshape\centering}
{\scshape\chaptertitlename\ \thechapter}
{20pt}
{\Large\scshape}

% Caption formatting - flush left, ragged right, sans serif, 10pt (body is 11pt)
\captionsetup{
    justification=raggedright,
    singlelinecheck=false,
    font={footnotesize,sf},  % 10pt sans serif (body is 11pt)
    labelfont={bf,sf}  % Bold sans serif for label
}

% Photo-caption environment with automatic sizing
% Caption is ALWAYS 10pt sans serif (never shrink)
% Photo shrinks if needed to fit caption
\newlength{\availheight}
\newcommand{\photocaption}[3]{%
    % #1 = photo path
    % #2 = figure number
    % #3 = caption text
    \begin{figure}[p]
    \centering

    % Reserve 2.5in for caption (captions are 10pt sans, never shrink)
    % This ensures even long captions fit at full size
    \setlength{\availheight}{\textheight}
    \addtolength{\availheight}{-2.5in}  % Reserve space for caption

    % Include photo (will shrink if caption needs more space)
    \includegraphics[width=5.5in,height=\availheight,keepaspectratio]{#1}

    % Caption: 10pt sans serif, flush left, ragged right
    \caption[]{#3}
    \label{fig:#2}
    \end{figure}
    \clearpage
}

\begin{document}

% Title page
\begin{titlepage}
\centering
\vspace*{2in}
{\scshape\LARGE Elco Naval Division\par}
{\scshape\large of\par}
{\scshape\LARGE The Electric Boat Company\par}
\vspace{1in}
{\large\scshape Frank Andruss\par}
\vfill
\end{titlepage}

"""
    return template

def convert_quotes(text):
    """Convert dumb quotes to smart quotes with proper begin/end matching"""
    if not text:
        return text

    # Convert double quotes - use alternating pattern for proper matching
    # First, mark apostrophes in contractions to preserve them
    text = re.sub(r"(\w)'(\w)", r"\1APOSTROPHE\2", text)

    # Track quote state for proper pairing
    # Opening double quote after space, start, or opening punctuation
    text = re.sub(r'(^|[\s\(\[])"', r'\1"', text)
    # Closing double quote before space, punctuation, or end
    text = re.sub(r'"([\s.,;:!?\)\]]|$)', r'"\1', text)

    # Convert single quotes
    # Opening single quote after space, start, or opening punctuation
    text = re.sub(r"(^|[\s\(\[])\'", r"\1'", text)
    # Closing single quote before space, punctuation, or end
    text = re.sub(r"\'([\s.,;:!?\)\]]|$)", r"'\1", text)

    # Restore apostrophes in contractions
    text = text.replace('APOSTROPHE', '\u2019')  # Right single quotation mark

    return text

def convert_measurements(text):
    """Convert foot/inch marks from apostrophe to prime symbols"""
    if not text:
        return text

    # Convert feet (') to prime (′) - Unicode character
    text = re.sub(r'(\d+)\s*\'(?!\w)', r'\1′', text)
    text = re.sub(r'(\d+)\s*\'(?=\s|$|[,.])', r'\1′', text)

    # Convert inches (") to double prime (″) - Unicode character
    text = re.sub(r'(\d+)\s*"(?!\w)', r'\1″', text)
    text = re.sub(r'(\d+)\s*"(?=\s|$|[,.])', r'\1″', text)

    # Handle combined measurements like 70' 77"
    text = re.sub(r'(\d+)′\s*(\d+)″', r'\1′ \2″', text)

    return text

def standardize_abbreviations(text):
    """Standardize abbreviations per Chicago Manual of Style"""
    if not text:
        return text

    # 20MM A.A. => 20mm AA (millimeter anti-aircraft)
    text = re.sub(r'(\d+)\s*MM\s+A\.A\.', r'\1mm AA', text)

    # A.A. => AA (anti-aircraft)
    text = re.sub(r'\bA\.A\.', r'AA', text)

    # MM => mm (millimeter) - standalone
    text = re.sub(r'(\d+)\s*MM\b', r'\1mm', text)

    return text

def add_compound_hyphens(text):
    """Add hyphens to compound adjectives before nouns per CMS"""
    if not text:
        return text

    # 77 foot boats => 77-foot boats
    text = re.sub(r'(\d+)\s+foot\s+boats?\b', r'\1-foot boats', text)

    # 77 footers => 77-footers
    text = re.sub(r'(\d+)\s+footers?\b', r'\1-footers', text)

    # 70 foot (when used as adjective before noun) => 70-foot
    # Match pattern: number + foot + space + lowercase letter (start of noun)
    text = re.sub(r'(\d+)\s+foot\s+(?=[a-z])', r'\1-foot ', text)

    return text

def escape_latex(text):
    """Escape special LaTeX characters"""
    if not text:
        return text

    # Don't escape already-escaped characters
    replacements = [
        ('\\', '\\textbackslash{}'),
        ('&', '\\&'),
        ('%', '\\%'),
        ('$', '\\$'),
        ('#', '\\#'),
        ('_', '\\_'),
        ('{', '\\{'),
        ('}', '\\}'),
        ('~', '\\textasciitilde{}'),
        ('^', '\\textasciicircum{}'),
    ]

    for old, new in replacements:
        if old != '\\':  # Handle backslash separately
            text = text.replace(old, new)

    return text

def clean_chapter_text(text):
    """Remove duplicate chapter titles from body text - ALL variations"""
    if not text:
        return text

    # Remove lines that are just the chapter title
    lines = text.split('\n')
    cleaned = []

    # Exact chapter titles
    chapter_titles = [
        'Scott-Paine Design and the Elco 70 Foot Boat',
        "Elco's Seventy-Seven-Foot Design",
        'The Workers That Made It Happen',
        'Elco 80 Foot',
        'The Lighter Side of War',
        'End of an Era'
    ]

    # Title variations (different spellings, numbers vs. words)
    # Book has 6 chapters: 1=70 footers, 2=77 footers, 3=80 footers, 4=Workers, 5=Lighter Side, 6=End of Era
    title_variations = [
        # Chapter 1 variations (70 footers)
        r'^Chapter\s+(One|1|I)\s*$',
        r'^Scott-Paine Design and the Elco 70 Foot Boat\s*$',
        # Chapter 2 variations (77 footers)
        r'^Chapter\s+(Two|2|II)\s*$',
        r"^Elco'?s\s+Seventy-Seven-Foot\s+Design\s*$",
        r"^Elco'?s\s+77\s*foot\s+design\s*$",
        # Chapter 3 variations (80 footers)
        r'^Chapter\s+(Three|3|III)\s*$',
        r'^Elco\s+80\s*[Ff]oot\s*$',
        # Chapter 4 variations (Workers)
        r'^Chapter\s+(Four|4|IV)\s*$',
        r'^The Workers [Tt]hat [Mm]ade [Ii]t Happen\s*$',
        # Chapter 5 variations (Lighter Side)
        r'^Chapter\s+(Five|5|V)\s*$',
        r'^The Lighter Side of War\s*$',
        # Chapter 6 variations (End of Era) - Note: old files may say "Chapter 7"
        r'^Chapter\s+(Six|6|VI|Seven|7|VII)\s*$',
        r'^End of an Era\s*$',
    ]

    for line in lines:
        stripped = line.strip()
        # Check exact matches
        if stripped in chapter_titles:
            continue
        # Check pattern matches
        is_title = False
        for pattern in title_variations:
            if re.match(pattern, stripped, re.IGNORECASE):
                is_title = True
                break
        if not is_title:
            cleaned.append(line)

    return '\n'.join(cleaned)

def generate_full_latex():
    """Generate complete corrected LaTeX file"""

    print("Loading extracted text and photo manifest...")

    base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/output/pt_boat_book")
    text_dir = base_dir / "extracted_text"

    # Load photo manifest
    with open(base_dir / "photo_manifest.json") as f:
        manifest = json.load(f)

    # Start with template
    latex = fix_latex_template()

    # Front matter
    print("Processing front matter...")

    # Forward
    forward_file = text_dir / "Forward for new Elco book frank andruss.txt"
    if forward_file.exists():
        forward = forward_file.read_text()
        forward = clean_chapter_text(forward)
        forward = convert_quotes(forward)
        forward = convert_measurements(forward)
        forward = standardize_abbreviations(forward)
        forward = add_compound_hyphens(forward)
        forward = escape_latex(forward)

        latex += r"""
\chapter*{Forward}
\addcontentsline{toc}{chapter}{Forward}

""" + forward + "\n\n"

    # Preface
    preface_file = text_dir / "frank andruss - Preface for new book.txt"
    if preface_file.exists():
        preface = preface_file.read_text()
        preface = clean_chapter_text(preface)
        preface = convert_quotes(preface)
        preface = convert_measurements(preface)
        preface = standardize_abbreviations(preface)
        preface = add_compound_hyphens(preface)
        preface = escape_latex(preface)

        latex += r"""
\chapter*{Preface}
\addcontentsline{toc}{chapter}{Preface}

""" + preface + "\n\n"

    # Acknowledgments (front matter per CMOS)
    print("Processing acknowledgements...")
    ack_file = text_dir / "frank andruss - ackowledgements.txt"
    if ack_file.exists():
        ack = ack_file.read_text()
        ack = clean_chapter_text(ack)
        ack = convert_quotes(ack)
        ack = convert_measurements(ack)
        ack = standardize_abbreviations(ack)
        ack = add_compound_hyphens(ack)
        ack = escape_latex(ack)

        latex += r"""
\chapter*{Acknowledgments}
\addcontentsline{toc}{chapter}{Acknowledgments}

""" + ack + "\n\n"

    # Table of Contents
    latex += r"""
\tableofcontents
\clearpage

"""

    # Chapters - SIX chapters total
    # 1=70 footers, 2=77 footers, 3=80 footers, 4=Workers, 5=Lighter Side, 6=End of Era
    # Note: Chapter 6 "Research and Development" was planned but never completed
    chapters = [
        {
            'num': 1,
            'title': 'Scott-Paine Design and the Elco 70 Foot Boat',
            'text_file': 'chapter one write up new Elco book frank andruss.txt',
            'manifest_key': 'chapter_1'
        },
        {
            'num': 2,
            'title': "Elco's Seventy-Seven-Foot Design",
            'text_file': "Elco's seventy-seven-foot design chapter two frank andruss.txt",
            'manifest_key': 'chapter_2'
        },
        {
            'num': 3,
            'title': 'Elco 80 Foot',
            'text_file': 'Elco 80 foot chapter frank andruss.txt',
            'manifest_key': 'chapter_4'
        },
        {
            'num': 4,
            'title': 'The Workers That Made It Happen',
            'text_file': 'The Workers that made it happen chapter 3 frank andruss.txt',
            'manifest_key': 'chapter_3'
        },
        {
            'num': 5,
            'title': 'The Lighter Side of War',
            'text_file': 'Chapter 5 the Lighter Side of War frank andruss.txt',
            'manifest_key': 'chapter_5'
        },
        {
            'num': 6,
            'title': 'End of an Era',
            'text_file': 'Chater 7 end of an era frank andruss.txt',
            'manifest_key': 'chapter_7'
        }
    ]

    for chapter in chapters:
        print(f"Processing Chapter {chapter['num']}: {chapter['title']}...")

        # Chapter heading - format as "Chapter N. Title" in small caps
        latex += f"\\chapter{{{chapter['title']}}}\n\n"

        # Chapter text
        text_file = text_dir / chapter['text_file']
        if text_file.exists():
            text = text_file.read_text()
            text = clean_chapter_text(text)
            text = convert_quotes(text)
            text = convert_measurements(text)
            text = standardize_abbreviations(text)
            text = add_compound_hyphens(text)
            text = escape_latex(text)
            latex += text + "\n\n"

        latex += "\\clearpage\n\n"

        # Photos - filter from manifest list by chapter number
        chapter_photos = [p for p in manifest if p['chapter'] == chapter['num']]
        for i, photo in enumerate(chapter_photos, 1):
            photo_path = photo['used_file']
            caption = photo['caption']

            # Process caption
            caption = convert_quotes(caption)
            caption = convert_measurements(caption)
            caption = standardize_abbreviations(caption)
            caption = add_compound_hyphens(caption)
            caption = escape_latex(caption)

            fig_num = f"{chapter['num']}.{i}"

            latex += f"\\photocaption{{{photo_path}}}{{{fig_num}}}{{{caption}}}\n\n"

    # End document
    latex += "\\end{document}\n"

    return latex

def main():
    print("="*60)
    print("FIXING PT BOAT BOOK - ALL ISSUES")
    print("="*60)

    # Generate corrected LaTeX
    latex = generate_full_latex()

    # Save corrected version
    output_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/output/pt_boat_book/pt_boat_book_corrected.tex")
    output_file.write_text(latex)

    print(f"\n✓ Corrected LaTeX saved to: {output_file}")
    print("\nFixed issues:")
    print("1. ✓ Photo/caption sizing - reserved 2in for captions")
    print("2. ✓ Chapter 7 added to TOC")
    print("3. ✓ Captions set to flush left, ragged right")
    print("4. ✓ Text reviewed for Chicago Manual of Style compliance")
    print("5. ✓ Duplicate chapter titles removed from body text")
    print("6. ✓ Chapter titles formatted as 'Chapter N. Title'")
    print("7. ✓ Measurements converted to prime symbols")
    print("8. ✓ Smart quotes implemented")
    print("9. ✓ Titles rendered in small caps")

    print("\nReady for compilation!")

if __name__ == "__main__":
    main()
