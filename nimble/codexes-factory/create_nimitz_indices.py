#!/usr/bin/env python3
"""
Create four comprehensive indices for Nimitz Graybook in LaTeX format.
Two-column layout using Warships & Navies template style.
"""

import json
from pathlib import Path
from typing import List, Dict


def load_entities():
    """Load extracted entities"""
    entities_file = Path("nimitz_ocr_gemini/entities_per_page/entities_all.json")

    with open(entities_file, 'r') as f:
        data = json.load(f)

    return data["entities"]


def load_page_mapping():
    """Load page mapping to get new page numbering"""
    mapping_file = Path("nimitz_ocr_gemini/page_mapping.json")

    with open(mapping_file, 'r') as f:
        data = json.load(f)

    return data["mapping"]


def create_index_latex(entity_type: str, entities: List[str], title: str) -> str:
    """Create LaTeX for a single index"""

    latex = []

    # Index header
    latex.append(r"\chapter{" + title + "}")
    latex.append(r"\label{index:" + entity_type + "}")
    latex.append(r"\markright{" + title + "}")  # Set odd-page header to index name
    latex.append("")
    latex.append(r"\begin{small}")
    latex.append(r"\begin{multicols}{2}")
    latex.append(r"\setlength{\columnwidth}{1.5in}")  # Default page width 1.5 inches per column
    latex.append("")

    # Add entities (alphabetically sorted)
    for entity in sorted(entities):
        # Escape special LaTeX characters
        entity_escaped = entity.replace("&", r"\&").replace("_", r"\_").replace("#", r"\#")

        # For now, just list the entity
        # TODO: Add page references once we link entities to pages
        latex.append(r"\noindent \textbf{" + entity_escaped + r"} \\")

    latex.append("")
    latex.append(r"\end{multicols}")
    latex.append(r"\end{small}")
    latex.append("")

    return "\n".join(latex)


def create_complete_indices_document():
    """Create complete LaTeX document with all four indices"""

    print("=" * 80)
    print("Creating Nimitz Graybook Indices")
    print("=" * 80)
    print()

    # Load data
    print("Loading extracted entities...")
    entities = load_entities()

    print(f"  Persons: {len(entities['persons']):,}")
    print(f"  Places: {len(entities['places']):,}")
    print(f"  Ships: {len(entities['ships']):,}")
    print(f"  Organizations: {len(entities['organizations']):,}")
    print(f"  TOTAL: {sum(len(v) for v in entities.values()):,}")
    print()

    # Create LaTeX document
    latex_parts = []

    # Document preamble
    latex_parts.append(r"""\documentclass[8.5in x 11in,11pt,twoside]{book}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{multicol}
\usepackage{fancyhdr}
\usepackage{titlesec}

% Page geometry for 8.5 x 11
\geometry{
    paperwidth=8.5in,
    paperheight=11in,
    margin=0.75in,
    top=1in,
    bottom=1in
}

% Headers and footers
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[LO]{\nouppercase{\rightmark}}  % Odd pages show index name
\fancyhead[RE]{Nimitz Graybook - Comprehensive Indices}  % Even pages show book title

% Chapter formatting
\titleformat{\chapter}[display]
{\normalfont\huge\bfseries}{\chaptertitlename\ \thechapter}{20pt}{\Huge}

\begin{document}

\frontmatter

\title{Command Summary of Fleet Admiral Chester W. Nimitz, USN\\
\large Comprehensive Indices}
\author{Compiled by Nimble Books LLC}
\date{2025}

\maketitle

\tableofcontents

\mainmatter

""")

    # Generate each index
    print("Generating indices...")

    print("  1. Index of Persons...")
    latex_parts.append(create_index_latex(
        "persons",
        entities["persons"],
        "Index of Persons"
    ))

    print("  2. Index of Places...")
    latex_parts.append(create_index_latex(
        "places",
        entities["places"],
        "Index of Places"
    ))

    print("  3. Index of Ships...")
    latex_parts.append(create_index_latex(
        "ships",
        entities["ships"],
        "Index of Ships"
    ))

    print("  4. Index of Organizations...")
    latex_parts.append(create_index_latex(
        "organizations",
        entities["organizations"],
        "Index of Organizations, Units, and Commands"
    ))

    # Document closing
    latex_parts.append(r"""
\end{document}
""")

    # Write LaTeX file
    output_file = Path("nimitz_ocr_gemini/nimitz_comprehensive_indices.tex")
    with open(output_file, 'w') as f:
        f.write("\n".join(latex_parts))

    print()
    print(f"✓ Created LaTeX file: {output_file}")
    print()

    # Compile to PDF
    print("Compiling to PDF...")
    import subprocess

    try:
        result = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", str(output_file)],
            cwd=output_file.parent,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            pdf_file = output_file.with_suffix('.pdf')
            print(f"✓ PDF created: {pdf_file}")

            # Get page count
            import fitz
            doc = fitz.open(pdf_file)
            print(f"  Total pages: {len(doc)}")
            doc.close()
        else:
            print("✗ PDF compilation failed")
            print(result.stdout[-500:] if result.stdout else "")
            print(result.stderr[-500:] if result.stderr else "")

    except Exception as e:
        print(f"✗ Error compiling PDF: {e}")

    print()
    print("=" * 80)
    print("INDICES CREATED")
    print("=" * 80)
    print()
    print(f"LaTeX source: {output_file}")
    print(f"Total entities indexed: {sum(len(v) for v in entities.values()):,}")
    print()
    print("Note: This is initial version without page references.")
    print("Next step: Link entities to page numbers for complete index.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    create_complete_indices_document()
