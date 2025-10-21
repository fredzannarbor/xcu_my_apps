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
            # Validate PDF page sizes (must be 8.5" x 11" portrait)
            try:
                self._validate_pdf_page_sizes(input_path)
            except ValueError as e:
                logger.error(f"❌ PDF validation failed: {e}")
                raise ValueError(f"PDF validation failed: {e}") from e

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

    def _validate_pdf_page_sizes(self, pdf_path: Path) -> None:
        """
        Validate that all pages in PDF are 8.5" x 11" portrait.

        Args:
            pdf_path: Path to PDF file to validate

        Raises:
            ValueError: If any page does not match required dimensions
        """
        # Expected dimensions in points (72 points per inch)
        EXPECTED_WIDTH = 8.5 * 72  # 612 points
        EXPECTED_HEIGHT = 11 * 72  # 792 points
        TOLERANCE = 2  # Allow 2 points tolerance for rounding

        logger.info(f"📏 Validating PDF page sizes: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            invalid_pages = []
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc[page_num]
                rect = page.rect
                width = rect.width
                height = rect.height

                # Check if page is portrait (height > width)
                is_portrait = height > width

                # Check if dimensions match expected size (within tolerance)
                width_match = abs(width - EXPECTED_WIDTH) <= TOLERANCE
                height_match = abs(height - EXPECTED_HEIGHT) <= TOLERANCE

                if not (is_portrait and width_match and height_match):
                    invalid_pages.append({
                        "page": page_num + 1,
                        "width_inches": round(width / 72, 2),
                        "height_inches": round(height / 72, 2),
                        "is_portrait": is_portrait
                    })

            doc.close()

            if invalid_pages:
                error_details = "\n".join([
                    f"  Page {p['page']}: {p['width_inches']}\" x {p['height_inches']}\" "
                    f"({'portrait' if p['is_portrait'] else 'landscape'})"
                    for p in invalid_pages
                ])
                error_msg = (
                    f"PDF contains {len(invalid_pages)} page(s) that are not 8.5\" x 11\" portrait:\n"
                    f"{error_details}\n"
                    f"All pages must be 8.5\" x 11\" portrait orientation."
                )
                raise ValueError(error_msg)

            logger.info(f"✅ All {total_pages} pages are 8.5\" x 11\" portrait")

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to validate PDF: {e}") from e

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
        """Generate LaTeX document that includes PDF body and AI-generated content."""
        title = escape_latex(metadata.get("title", "Untitled"))
        author = escape_latex(metadata.get("author", "Unknown Author"))

        # Check if we have pipeline content
        pipeline_content = metadata.get("_pipeline_content", {})
        has_pipeline_content = bool(pipeline_content)

        if has_pipeline_content:
            logger.info("✅ Including AI-generated content from pipeline in LaTeX document")
        else:
            logger.info("✅ Generated minimal LaTeX template for PDF body inclusion")

        # --- Copyright Page Content ---
        # Check for assigned ISBN first, then fallback to other fields
        isbn = metadata.get('assigned_isbn') or metadata.get('isbn13') or metadata.get('isbn')
        if isbn and isbn != "Unknown" and isbn != "TBD":
            # Use ISBNFormatter for proper hyphenation and validation
            try:
                try:
                    from codexes.modules.metadata.isbn_formatter import ISBNFormatter
                except ModuleNotFoundError:
                    from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter

                isbn_formatter = ISBNFormatter()

                # Generate properly formatted ISBN for copyright page
                formatted_isbn = isbn_formatter.generate_copyright_page_isbn(isbn)
                isbn_line = f"{escape_latex(formatted_isbn)}\\\\[2em]"
                logger.info(f"✅ Using formatted ISBN for copyright page: {formatted_isbn}")
            except Exception as e:
                logger.warning(f"ISBN formatting failed, using original: {e}")
                isbn_line = f"ISBN: {escape_latex(isbn)}\\\\[2em]"
                logger.info(f"✅ Using original ISBN for copyright page: {isbn}")
        else:
            isbn_line = ""
            logger.info("No valid ISBN found for copyright page")

        version = escape_latex(f"v1.0-{datetime.now().strftime('%Y%m%d')}")
        copyright_year = datetime.now().year

        # Extract keywords for copyright page
        keywords_section = ""
        if has_pipeline_content:
            front_matter_data = pipeline_content.get("front_matter", {})
            if "bibliographic_key_phrases" in front_matter_data:
                keywords = self._extract_content(front_matter_data["bibliographic_key_phrases"])
                if keywords:
                    keywords_latex = escape_latex(keywords)
                    keywords_section = f"""
\\subsection*{{Subject Headings}}
{keywords_latex}"""
                    logger.info("✅ Including bibliographic keywords on copyright page")

        copyright_content = f"""\\newpage
\\thispagestyle{{empty}}
\\vspace*{{1in}}
\\begin{{center}}
\\large
Nimble Ultra is an imprint of Nimble Books LLC.\\\\
Ann Arbor, Michigan, USA\\\\
http://NimbleBooks.com\\\\
Inquiries: info@nimblebooks.com\\\\[2em]
Copyright \\copyright {copyright_year} by Nimble Books LLC. All rights reserved.\\\\[2em]
{isbn_line}
Version: {version}
\\end{{center}}
{keywords_section}"""

        # --- Table of Contents (page iii-iv) - ends on even page for roman v start ---
        toc_content = """\\newpage
\\thispagestyle{{empty}}
\\tableofcontents*
\\cleardoublepage"""

        # --- Build Front Matter Sections ---
        front_matter_sections = ""
        if has_pipeline_content:
            front_matter_data = pipeline_content.get("front_matter", {})

            # Motivation
            if "motivation" in front_matter_data:
                motivation_content = self._extract_content(front_matter_data["motivation"])
                if motivation_content:
                    front_matter_sections += self._format_section(
                        "Motivation",
                        motivation_content,
                        use_markdown=True
                    )

            # Historical Context
            if "historical_context" in front_matter_data:
                context_content = self._extract_content(front_matter_data["historical_context"])
                if context_content:
                    front_matter_sections += self._format_section(
                        "Historical Context",
                        context_content,
                        use_markdown=True
                    )

            # Abstracts (before Mnemonics)
            if "abstracts_x4" in front_matter_data:
                abstracts_content = self._extract_content(front_matter_data["abstracts_x4"])
                if abstracts_content:
                    front_matter_sections += self._format_section(
                        "Abstracts",
                        abstracts_content,
                        use_markdown=True
                    )

            # Mnemonics (special handling for LaTeX)
            if "mnemonics" in front_matter_data:
                mnemonics_content = self._extract_mnemonics(front_matter_data["mnemonics"])
                if mnemonics_content:
                    # Mnemonics already contain LaTeX, don't convert
                    # Ensure it's inserted directly and ends with cleardoublepage
                    if not mnemonics_content.strip().endswith("\\cleardoublepage"):
                        mnemonics_content = mnemonics_content.rstrip() + "\n\\cleardoublepage\n"
                    front_matter_sections += f"\n{mnemonics_content}\n"

            # Important Passages
            if "important_passages" in front_matter_data:
                passages_content = self._extract_content(front_matter_data["important_passages"])
                if passages_content:
                    front_matter_sections += self._format_section(
                        "Important Passages",
                        passages_content,
                        use_markdown=True
                    )

        # --- Back Matter Intro Page ---
        back_matter_intro = """\\backmatter
\\chapter*{Back Matter}
\\addcontentsline{toc}{chapter}{Back Matter}

This section contains supplementary materials including indices to help readers navigate the document.
\\cleardoublepage

% Custom footer for back matter with "Back Matter - N" format
\\makeoddfoot{mypagestyle}{}{Back Matter~-~}{\\thepage}
\\makeevenfoot{mypagestyle}{\\thepage}{Back Matter~-~}{}
"""

        # --- Build Back Matter Sections ---
        back_matter_sections = ""
        if has_pipeline_content:
            back_matter_data = pipeline_content.get("back_matter", {})

            # Index of Persons
            if "index_persons" in back_matter_data:
                persons_content = self._extract_content(back_matter_data["index_persons"])
                if persons_content:
                    back_matter_sections += self._format_section(
                        "Index of Persons",
                        persons_content,
                        use_markdown=True
                    )

            # Index of Places
            if "index_places" in back_matter_data:
                places_content = self._extract_content(back_matter_data["index_places"])
                if places_content:
                    back_matter_sections += self._format_section(
                        "Index of Places",
                        places_content,
                        use_markdown=True
                    )

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

% --- Title page (i) - unnumbered ---
\\thispagestyle{{empty}}
\\begin{{titlingpage}}
\\begin{{center}}
\\vspace*{{\\fill}}
{{\\Huge\\bfseries {title}}}\\\\[1cm]
{{\\Large {author}}}\\\\[2cm]
\\vspace*{{\\fill}}
\\end{{center}}
\\end{{titlingpage}}

% --- Copyright page (ii) - unnumbered ---
{copyright_content}

% --- Table of Contents (iii-iv) - unnumbered, ends on even page ---
{toc_content}

% --- Start roman numerals at page v for front matter ---
\\pagenumbering{{roman}}
\\setcounter{{page}}{{5}}
\\pagestyle{{mypagestyle}}

{front_matter_sections}

% --- Main matter - switch to arabic numerals ---
\\mainmatter
\\IfFileExists{{pdf_body_source.pdf}}{{%
  \\includepdf[pages=-,pagecommand={{}}]{{pdf_body_source.pdf}}
}}{{%
  \\chapter{{Content}}
  \\textit{{No PDF content found. The original PDF should be included here.}}
}}

% --- Back matter with custom numbering ---
{back_matter_intro}

{back_matter_sections}

\\end{{document}}
"""

    def _extract_content(self, section_data: Dict[str, Any]) -> str:
        """
        Extract content from a pipeline section, handling JSON and errors gracefully.

        Args:
            section_data: Section data from pipeline with 'content' key

        Returns:
            Extracted content string, or empty string if extraction fails
        """
        if not section_data or "content" not in section_data:
            return ""

        content = section_data["content"]

        # Handle dict content directly
        if isinstance(content, dict):
            if "error" in content:
                logger.warning(f"Skipping section with error: {content.get('error', 'Unknown error')}")
                return ""
            # Try common content keys
            for key in ["keywords", "text", "content", "motivation", "context", "passages", "persons", "places"]:
                if key in content:
                    return str(content[key])
            # If no specific key found, return the whole dict as string (will be ugly but visible)
            logger.warning(f"No recognized content key in dict, available keys: {list(content.keys())}")
            return str(content)

        # Check for errors in string content
        if isinstance(content, str):
            try:
                content_json = json.loads(content)
                if isinstance(content_json, dict) and "error" in content_json:
                    logger.warning(f"Skipping section with error: {content_json.get('error', 'Unknown error')}")
                    return ""
                # If it's a dict with specific content keys, extract them
                if isinstance(content_json, dict):
                    # Try common content keys
                    for key in ["keywords", "text", "content", "motivation", "context", "passages", "persons", "places"]:
                        if key in content_json:
                            return str(content_json[key])
                    # If no specific key found, return the whole JSON as string
                    logger.warning(f"No recognized content key in parsed JSON, available keys: {list(content_json.keys())}")
                    return str(content_json)
            except json.JSONDecodeError:
                # Not JSON, return as-is
                pass

        return str(content)

    def _extract_mnemonics(self, section_data: Dict[str, Any]) -> str:
        """
        Extract mnemonics content, which is already in LaTeX format.

        Args:
            section_data: Section data from pipeline with 'content' key

        Returns:
            LaTeX content string, or empty string if extraction fails
        """
        if not section_data or "content" not in section_data:
            return ""

        content = section_data["content"]

        # Check for errors
        if isinstance(content, dict):
            if "error" in content:
                logger.warning(f"Skipping mnemonics with error: {content.get('error', 'Unknown error')}")
                return ""
            # Extract mnemonics_tex field
            if "mnemonics_tex" in content:
                return content["mnemonics_tex"]
            # If content is a dict but doesn't have mnemonics_tex, it's an error
            logger.warning(f"Mnemonics content is a dict but missing 'mnemonics_tex' field: {list(content.keys())}")
            return ""

        if isinstance(content, str):
            try:
                content_json = json.loads(content)
                if isinstance(content_json, dict):
                    if "error" in content_json:
                        logger.warning(f"Skipping mnemonics with error: {content_json.get('error', 'Unknown error')}")
                        return ""
                    # Extract mnemonics_tex field
                    if "mnemonics_tex" in content_json:
                        return content_json["mnemonics_tex"]
            except json.JSONDecodeError:
                # Not JSON, return as-is (might already be LaTeX)
                pass

        return str(content)

    def _format_section(self, title: str, content: str, use_markdown: bool = True) -> str:
        """
        Format a section with title and content for LaTeX inclusion.

        Args:
            title: Section title
            content: Section content
            use_markdown: If True, convert markdown to LaTeX

        Returns:
            Formatted LaTeX section
        """
        if not content.strip():
            return ""

        escaped_title = escape_latex(title)

        # Convert content if needed
        if use_markdown:
            # Skip first heading if it matches the chapter title
            latex_content = markdown_to_latex(content, skip_first_heading_if_matches=title)
        else:
            latex_content = content

        return f"""
\\chapter*{{{escaped_title}}}
\\addcontentsline{{toc}}{{chapter}}{{{escaped_title}}}

{latex_content}
\\cleardoublepage
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
