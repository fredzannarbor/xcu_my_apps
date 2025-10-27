#!/usr/bin/env python3
"""Build PT Boat Book - Complete LaTeX Generation"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

# Directories
SOURCE_DIR = Path("/Users/fred/Downloads/Files for New PT book")
OUTPUT_DIR = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/output/pt_boat_book")
TEXT_DIR = OUTPUT_DIR / "extracted_text"

# Chapter configuration
CHAPTERS = [
    {
        'num': 1,
        'title': "Scott-Paine Design and the Elco 70 Foot Boat",
        'text_file': "chapter one write up new Elco book frank andruss.txt",
        'caption_file': "Chapter One Photo Descriptions frank andruss.txt",
        'photo_dir': "2025-04-12 22.31.21 - chapter one photos -A frank andruss",
        'photo_count': 20
    },
    {
        'num': 2,
        'title': "Elco's Seventy-Seven-Foot Design",
        'text_file': "Elco's seventy-seven-foot design chapter two frank andruss.txt",
        'caption_file': "chapter twp photo descriptions 2nd one frank andruss.txt",
        'photo_dir': "chapter two photos -2 frank andruss",
        'photo_count': 36
    },
    {
        'num': 3,
        'title': "The Workers That Made It Happen",
        'text_file': "The Workers that made it happen chapter 3 frank andruss.txt",
        'caption_file': "chapter three photo descriptions frank andruss.txt",
        'photo_dir': "chapter 3 photos frank andruss",
        'photo_count': 26
    },
    {
        'num': 4,
        'title': "Elco 80 Foot",
        'text_file': "Elco 80 foot chapter frank andruss.txt",
        'caption_file': "chapter four photo descriptions second time frank andruss.txt",
        'photo_dir': "Chapter 4 photos -1 frank andruss",
        'photo_count': 19
    },
    {
        'num': 5,
        'title': "The Lighter Side of War",
        'text_file': "Chapter 5 the Lighter Side of War frank andruss.txt",
        'caption_file': "Chapter five photo discriptions (2) frank andruss.txt",
        'photo_dir': "chapter 5 photos frank andruss",
        'photo_count': 16
    },
    {
        'num': 7,
        'title': "End of an Era",
        'text_file': "Chater 7 end of an era frank andruss.txt",
        'caption_file': "chapter 7 photo descriptions frank andruss.txt",
        'photo_dir': "chapter 7 photos frank andruss",
        'photo_count': 38
    }
]


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    # First handle backslash separately
    text = text.replace('\\', r'\textbackslash{}')
    for char, replacement in replacements.items():
        if char != '\\':
            text = text.replace(char, replacement)
    return text


def parse_captions(caption_file: Path) -> Dict[str, str]:
    """Parse caption file to extract photo number -> caption mapping."""
    captions = {}

    with open(caption_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by photo numbers (e.g., "1.", "2.", "12b.", etc.)
    # Pattern: number followed by optional letter, followed by period
    pattern = r'^(\d+[a-z]?)\.\s+'

    lines = content.split('\n')
    current_num = None
    current_caption = []

    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            # Save previous caption
            if current_num and current_caption:
                captions[current_num] = ' '.join(current_caption).strip()

            # Start new caption
            current_num = match.group(1)
            # Get text after the number
            caption_text = re.sub(pattern, '', line.strip())
            current_caption = [caption_text] if caption_text else []
        elif current_num and line.strip():
            current_caption.append(line.strip())

    # Save last caption
    if current_num and current_caption:
        captions[current_num] = ' '.join(current_caption).strip()

    return captions


def get_photo_files(photo_dir: Path) -> List[Path]:
    """Get all photo files from directory, sorted properly."""
    if not photo_dir.exists():
        print(f"Warning: Photo directory not found: {photo_dir}")
        return []

    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.tif', '.tiff', '.png'}
    photos = [f for f in photo_dir.iterdir()
              if f.suffix.lower() in image_extensions]

    # Sort by natural order (handles numbers correctly)
    def natural_sort_key(path):
        # Extract number from filename
        match = re.search(r'(\d+)([a-z]?)', path.stem.lower())
        if match:
            num = int(match.group(1))
            letter = match.group(2) or ''
            return (num, letter)
        return (0, '')

    photos.sort(key=natural_sort_key)
    return photos


def match_photo_to_caption(photo_path: Path, captions: Dict[str, str]) -> Tuple[str, str]:
    """Match a photo file to its caption."""
    # Extract photo number from filename
    filename = photo_path.stem.lower()
    match = re.search(r'photo\s+(\d+[a-z]?)', filename)

    if match:
        photo_num = match.group(1)
        caption = captions.get(photo_num, f"Photo {photo_num} (caption not found)")
        return photo_num, caption

    # Fallback: use filename
    return filename, f"Caption for {photo_path.name} not found"


def convert_to_jpg_if_needed(photo_path: Path, output_dir: Path) -> Path:
    """Convert TIF/TIFF to JPG if needed, return path to use."""
    if photo_path.suffix.lower() in ['.tif', '.tiff']:
        # Convert to JPG
        jpg_path = output_dir / f"{photo_path.stem}.jpg"
        if not jpg_path.exists():
            try:
                # Use ImageMagick or Python PIL
                subprocess.run([
                    'convert', str(photo_path),
                    '-quality', '90',
                    str(jpg_path)
                ], check=True, capture_output=True)
                print(f"Converted: {photo_path.name} -> {jpg_path.name}")
                return jpg_path
            except subprocess.CalledProcessError:
                # Try with sips (macOS)
                try:
                    subprocess.run([
                        'sips', '-s', 'format', 'jpeg',
                        str(photo_path), '--out', str(jpg_path)
                    ], check=True, capture_output=True)
                    print(f"Converted with sips: {photo_path.name} -> {jpg_path.name}")
                    return jpg_path
                except:
                    print(f"Warning: Could not convert {photo_path.name}, using original")
                    return photo_path
        return jpg_path
    return photo_path


def build_latex_document():
    """Build the complete LaTeX document."""

    # Create photos directory for converted images
    photos_output_dir = OUTPUT_DIR / "photos"
    photos_output_dir.mkdir(exist_ok=True)

    # Read title
    with open(TEXT_DIR / "Title of the new book frank andruss.txt", 'r') as f:
        title_lines = [line.strip() for line in f.readlines() if line.strip()]
        book_title = "\\\\".join(title_lines)

    # Read forward and preface
    with open(TEXT_DIR / "Forward for new Elco book frank andruss.txt", 'r') as f:
        forward_text = f.read()

    with open(TEXT_DIR / "frank andruss - Preface for new book.txt", 'r') as f:
        preface_text = f.read()

    with open(TEXT_DIR / "frank andruss - ackowledgements.txt", 'r') as f:
        acknowledgements_text = f.read()

    # Start building LaTeX
    latex = []

    # Document class and packages
    latex.append(r'''\documentclass[11pt]{book}
\usepackage[paperwidth=7in, paperheight=10in, margin=0.75in, top=1in, bottom=1in]{geometry}
\usepackage{graphicx}
\usepackage{caption}
\usepackage{float}
\usepackage{setspace}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% Chapter formatting
\titleformat{\chapter}[display]
  {\normalfont\huge\bfseries}{\chaptertitlename\ \thechapter}{20pt}{\Huge}
\titlespacing*{\chapter}{0pt}{0pt}{40pt}

% Photo caption formatting
\captionsetup{
  font=small,
  labelfont=bf,
  textfont=it,
  justification=centering,
  singlelinecheck=false,
  format=plain
}

% Page style
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\leftmark}
\fancyhead[LO]{\rightmark}
\renewcommand{\headrulewidth}{0.4pt}

% Start document
\begin{document}

% Front matter
\frontmatter
''')

    # Title page
    latex.append(r'''
\begin{titlepage}
\centering
\vspace*{2in}
{\Huge\bfseries ''' + book_title + r''' \par}
\vspace{1in}
{\Large Frank Andruss\par}
\vfill
\end{titlepage}
''')

    # Forward
    latex.append(r'''
\chapter*{Forward}
\addcontentsline{toc}{chapter}{Forward}
''' + escape_latex(forward_text) + '\n\n')

    # Preface
    latex.append(r'''
\chapter*{Preface}
\addcontentsline{toc}{chapter}{Preface}
''' + escape_latex(preface_text) + '\n\n')

    # Table of contents
    latex.append(r'''
\tableofcontents
\clearpage
''')

    # Main matter
    latex.append(r'''
\mainmatter
''')

    # Build photo manifest
    photo_manifest = []

    # Process each chapter
    for chapter in CHAPTERS:
        print(f"\nProcessing Chapter {chapter['num']}: {chapter['title']}")

        # Read chapter text
        chapter_text_file = TEXT_DIR / chapter['text_file']
        with open(chapter_text_file, 'r') as f:
            chapter_text = f.read()

        # Parse captions
        caption_file = TEXT_DIR / chapter['caption_file']
        captions = parse_captions(caption_file)
        print(f"  Found {len(captions)} captions")

        # Get photo files
        photo_dir = SOURCE_DIR / chapter['photo_dir']
        photos = get_photo_files(photo_dir)
        print(f"  Found {len(photos)} photos")

        # Start chapter
        latex.append(f"\n\\chapter{{{chapter['title']}}}\n\n")
        latex.append(escape_latex(chapter_text) + '\n\n')
        latex.append(r'\clearpage' + '\n\n')

        # Add photos
        for photo in photos:
            photo_num, caption = match_photo_to_caption(photo, captions)

            # Convert if needed
            photo_to_use = convert_to_jpg_if_needed(photo, photos_output_dir)

            # Add to manifest
            photo_manifest.append({
                'chapter': chapter['num'],
                'photo_num': photo_num,
                'original_file': str(photo),
                'used_file': str(photo_to_use),
                'caption': caption
            })

            # Add to LaTeX
            latex.append(r'''
\begin{figure}[p]
\centering
\includegraphics[width=5.5in,height=8in,keepaspectratio]{''' + str(photo_to_use) + r'''}
\caption{''' + escape_latex(caption) + r'''}
\end{figure}
\clearpage
''')

        print(f"  Processed {len(photos)} photos for Chapter {chapter['num']}")

    # Back matter
    latex.append(r'''
\backmatter

\chapter*{Acknowledgements}
\addcontentsline{toc}{chapter}{Acknowledgements}
''' + escape_latex(acknowledgements_text) + '\n\n')

    # End document
    latex.append(r'\end{document}')

    # Write LaTeX file
    latex_file = OUTPUT_DIR / "pt_boat_book.tex"
    with open(latex_file, 'w', encoding='utf-8') as f:
        f.write(''.join(latex))

    print(f"\nLaTeX file created: {latex_file}")

    # Write photo manifest
    manifest_file = OUTPUT_DIR / "photo_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(photo_manifest, f, indent=2)

    print(f"Photo manifest created: {manifest_file}")
    print(f"Total photos in manifest: {len(photo_manifest)}")

    return latex_file, manifest_file


def compile_latex(latex_file: Path):
    """Compile LaTeX to PDF using lualatex."""
    print(f"\nCompiling LaTeX to PDF...")

    # Change to output directory
    os.chdir(OUTPUT_DIR)

    # Run lualatex twice (for TOC)
    for i in range(2):
        print(f"  Pass {i+1}/2...")
        result = subprocess.run(
            ['lualatex', '-interaction=nonstopmode', latex_file.name],
            capture_output=True,
            text=True
        )

        # Save log
        if i == 1:  # Save final log
            log_file = OUTPUT_DIR / "build_log.txt"
            with open(log_file, 'w') as f:
                f.write(result.stdout)
                f.write("\n\n=== STDERR ===\n\n")
                f.write(result.stderr)

            print(f"  Build log saved: {log_file}")

    pdf_file = OUTPUT_DIR / "pt_boat_book.pdf"
    if pdf_file.exists():
        print(f"\nPDF created successfully: {pdf_file}")
        print(f"PDF size: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
        return pdf_file
    else:
        print("\nERROR: PDF compilation failed!")
        print("Check build_log.txt for details")
        return None


def main():
    """Main execution."""
    print("=" * 60)
    print("PT BOAT BOOK BUILDER")
    print("=" * 60)

    # Build LaTeX document
    latex_file, manifest_file = build_latex_document()

    # Compile to PDF
    pdf_file = compile_latex(latex_file)

    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  LaTeX source: {latex_file}")
    print(f"  PDF: {pdf_file if pdf_file else 'FAILED'}")
    print(f"  Photo manifest: {manifest_file}")
    print(f"  Build log: {OUTPUT_DIR / 'build_log.txt'}")
    print(f"\nAll files in: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
