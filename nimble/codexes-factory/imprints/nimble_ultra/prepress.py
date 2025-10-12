#!/usr/bin/env python3
"""
Prepress processor for Nimble Ultra Global
Customized content processor for this imprint's specific needs.
"""

import logging
import json
import re
import shutil
import uuid
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import fitz  # PyMuPDF

# Import base prepress utilities
try:
    from codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from codexes.modules.covers.cover_generator import create_cover_latex
    from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from codexes.modules.distribution.quote_processor import QuoteProcessor
except ModuleNotFoundError:
    from src.codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from src.codexes.modules.covers.cover_generator import create_cover_latex
    from src.codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from src.codexes.modules.distribution.quote_processor import QuoteProcessor

logger = logging.getLogger(__name__)

# Imprint-specific configuration
IMPRINT_CONFIG = {
    "name": "Nimble Ultra Global",
    "publisher": "Nimble Books LLC",
    "focus": ["History", "Political Science", "Military", "Government"],
    "target_audience": "General Adult, Academic, and Professional",
    "specialized_processing": True
}

class NimbleUltraGlobalProcessor:
    """
    Specialized prepress processor for Nimble Ultra Global.
    Handles content processing specific to this imprint's focus areas.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the processor with imprint-specific settings."""
        self.imprint_config = IMPRINT_CONFIG
        self.template_dir = Path(__file__).parent

    def process_manuscript(self, input_path: str, output_dir: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Process manuscript for Nimble Ultra Global publication.

        Args:
            input_path: Path to input manuscript
            output_dir: Directory for output files
            metadata: Book metadata dictionary

        Returns:
            Dictionary with paths to generated files
        """
        logger.info(f"Processing manuscript for {self.imprint_config['name']}")

        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # Check if input is a PDF for direct inclusion
        if input_path.suffix.lower() == '.pdf':
            # Copy PDF to build directory for inclusion
            pdf_body_path = output_dir / "pdf_body_source.pdf"
            shutil.copy2(input_path, pdf_body_path)
            logger.info(f"✅ Copied PDF body source to {pdf_body_path}")

            # Generate minimal LaTeX content (front matter + back matter only)
            latex_content = self._generate_latex_with_pdf_body(metadata)
            results["pdf_body_source"] = str(pdf_body_path)
        else:
            # Load and process manuscript content
            content = self._load_manuscript(input_path)
            content = self._apply_imprint_formatting(content)

            # Generate LaTeX content
            latex_content = self._generate_latex(content, metadata)

        latex_path = output_dir / "manuscript.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        results["latex"] = str(latex_path)

        # Compile to PDF
        pdf_path = compile_tex_to_pdf(latex_path, output_dir)
        if pdf_path:
            results["pdf"] = pdf_path

        # Generate cover
        cover_path = self._generate_cover(metadata, output_dir)
        if cover_path:
            results["cover"] = cover_path

        return results

    def _load_manuscript(self, input_path: Path) -> str:
        """Load manuscript content from various formats."""
        if input_path.suffix.lower() == '.md':
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif input_path.suffix.lower() == '.txt':
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif input_path.suffix.lower() == '.pdf':
            # PDF files are handled separately for direct inclusion
            raise ValueError(f"PDF files should be handled by PDF inclusion path, not text loading")
        else:
            raise ValueError(f"Unsupported input format: {input_path.suffix}")

    def _apply_imprint_formatting(self, content: str) -> str:
        """Apply Nimble Ultra Global-specific formatting rules."""
        # Apply intelligence document formatting
        # Add redacted text styling
        content = re.sub(r'\[REDACTED\]', r'\\textcolor{gray}{[REDACTED]}', content)

        # Format speaker tags for oral history sections
        content = re.sub(r'^([A-Z][A-Z\s]+):', r'\\textbf{\1:}', content, flags=re.MULTILINE)

        # Add annotation markers
        content = re.sub(r'\*\*Note:\*\*', r'\\marginpar{\\textit{Note:}}', content)

        return content

    def _generate_latex(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate LaTeX document using imprint template."""
        # Load template
        template_path = self.template_dir / "template.tex"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Convert content to LaTeX
        latex_content = markdown_to_latex(content)

        # Replace template variables
        template_vars = {
            "booktitle": escape_latex(metadata.get("title", "Untitled")),
            "booksubtitle": escape_latex(metadata.get("subtitle", "")),
            "bookauthor": escape_latex(metadata.get("author", "Unknown Author")),
            "bookyear": str(datetime.now().year),
            "bookisbn": metadata.get("isbn", ""),
            "content": latex_content
        }

        for var, value in template_vars.items():
            template = template.replace("\\{" + var + "}", str(value))

        return template

    def _generate_latex_with_pdf_body(self, metadata: Dict[str, Any]) -> str:
        """Generate LaTeX document that includes PDF body."""
        title = escape_latex(metadata.get("title", "Untitled"))
        author = escape_latex(metadata.get("author", "Unknown Author"))

        # Use a PDF-specific template that doesn't require front matter files
        logger.info("✅ Generated minimal LaTeX template for PDF body inclusion")
        return f"""\\documentclass[11pt,twoside]{{memoir}}
\\normalsize

% --- Page Geometry ---
\\setstocksize{{9in}}{{6in}}
\\settrimmedsize{{9in}}{{6in}}{{*}}
\\settrims{{0pt}}{{0pt}}

\\setlrmarginsandblock{{1in}}{{1in}}{{*}}
\\setulmarginsandblock{{0.75in}}{{*}}{{1}}

\\setheadfoot{{24pt}}{{24pt}}
\\setlength{{\\headdrop}}{{2pt}}
\\setlength{{\\headsep}}{{12pt}}
\\checkandfixthelayout
\\frenchspacing

% --- Font Setup ---
\\usepackage{{fontspec}}
\\setmainfont{{Adobe Caslon Pro}}
\\setsansfont{{Neulis Sans}}

% --- Packages ---
\\usepackage{{pdfpages}}
\\usepackage{{microtype}}
\\usepackage{{xcolor}}
\\usepackage{{graphicx}}

% --- Page Style Setup ---
\\makepagestyle{{mypagestyle}}
\\makeoddhead{{mypagestyle}}{{}}{{}}{{\\large\\scshape\\sffamily {title}}}
\\makeevenhead{{mypagestyle}}{{\\small\\textit{{{author}}}}}{{}}{{}}
\\makeoddfoot{{mypagestyle}}{{}}{{}}{{\\thepage}}
\\makeevenfoot{{mypagestyle}}{{\\thepage}}{{}}{{}}
\\pagestyle{{mypagestyle}}

\\begin{{document}}

% Simple title page
\\frontmatter
\\begin{{titlingpage}}
\\begin{{center}}
\\vspace*{{\\fill}}
{{\\Huge\\bfseries {title}}}\\\\[1cm]
{{\\Large {author}}}\\\\[2cm]
\\vspace*{{\\fill}}
\\end{{center}}
\\end{{titlingpage}}

% Include the PDF as main content
\\mainmatter
\\IfFileExists{{pdf_body_source.pdf}}{{%
  \\includepdf[pages=-,pagecommand={{}}]{{pdf_body_source.pdf}}
}}{{%
  \\chapter{{Content}}
  \\textit{{No PDF content found. The original PDF should be included here.}}
}}

\\end{{document}}
"""

    def _generate_cover(self, metadata: Dict[str, Any], output_dir: Path) -> Optional[str]:
        """Generate cover using imprint template."""
        try:
            cover_template = self.template_dir / "cover_template.tex"
            if cover_template.exists():
                return create_cover_latex(metadata, str(cover_template), str(output_dir))
        except Exception as e:
            logger.warning(f"Cover generation failed: {e}")
        return None

def main():
    """CLI interface for the prepress processor."""
    import argparse

    parser = argparse.ArgumentParser(description="Process manuscript for Nimble Ultra Global")
    parser.add_argument("input", help="Input manuscript file")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("--metadata", help="JSON file with book metadata")

    args = parser.parse_args()

    # Load metadata
    metadata = {}
    if args.metadata and Path(args.metadata).exists():
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)

    # Process manuscript
    processor = NimbleUltraGlobalProcessor()
    results = processor.process_manuscript(args.input, args.output, metadata)

    print("Processing complete:")
    for file_type, path in results.items():
        print(f"  {file_type}: {path}")

def process_single_book(
        json_path: Path,
        final_output_dir: Path,
        templates_dir: Path,
        debug_cover: bool = False,
        catalog_only: bool = False,
        leave_build_directories_in_place: bool = False,
        config: Dict[str, Any] = None
) -> Optional[Dict]:
    """
    Orchestrates the full prepress process for a single book in Nimble Ultra imprint.
    Handles both regular manuscript processing and PDF body source inclusion.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Processing book: {data.get('title', 'Unknown')}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not read or parse JSON file at {json_path}: {e}")
        return None

    # Initialize processor
    processor = NimbleUltraGlobalProcessor()

    # Check if there's a body_source in the data
    body_source = data.get('body_source')

    if body_source and Path(body_source).exists():
        logger.info(f"📄 Processing with body source: {body_source}")

        # Use the processor's process_manuscript method which handles PDFs
        try:
            results = processor.process_manuscript(
                input_path=str(body_source),
                output_dir=str(final_output_dir),
                metadata=data
            )

            # Return results in the expected format for the pipeline
            return {
                "status": "success",
                "pdf_path": results.get("pdf"),
                "cover_path": results.get("cover"),
                "page_count": data.get("pages", 100),  # Default or from metadata
                "processed_file": str(json_path),
                "output_dir": str(final_output_dir)
            }

        except Exception as e:
            logger.error(f"❌ Error processing body source {body_source}: {e}")
            return None
    else:
        logger.info("📝 No body source found, using default content generation")
        # For now, return basic success - this could be expanded for content generation
        return {
            "status": "success",
            "processed_file": str(json_path),
            "output_dir": str(final_output_dir),
            "page_count": data.get("pages", 100)
        }


if __name__ == "__main__":
    main()
