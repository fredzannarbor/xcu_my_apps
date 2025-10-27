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
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Import base prepress utilities
try:
    from codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from codexes.modules.prepress.markdown_to_latex import (
        convert_index_markdown_to_latex,
        convert_mnemonics_markdown_to_latex
    )
    from codexes.modules.covers.cover_generator import create_cover_latex
    from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from codexes.modules.distribution.quote_processor import QuoteProcessor
except ModuleNotFoundError:
    from src.codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from src.codexes.modules.prepress.markdown_to_latex import (
        convert_index_markdown_to_latex,
        convert_mnemonics_markdown_to_latex
    )
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

        # Initialize Jinja2 environment for template-based LaTeX generation
        templates_path = self.template_dir / "templates"
        self.jinja_env = None
        if templates_path.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(templates_path)),
                autoescape=False,  # LaTeX needs manual escaping
                trim_blocks=True,
                lstrip_blocks=True
            )
            # Add custom filters
            self.jinja_env.filters['escape_latex'] = escape_latex
            self.jinja_env.filters['markdown_to_latex'] = markdown_to_latex
            self.jinja_env.filters['preprocess_markdown'] = self._preprocess_markdown
            self.jinja_env.filters['markdown_to_latex_skip_first'] = self._markdown_to_latex_skip_first
            self.jinja_env.filters['first_value'] = lambda d: list(d.values())[0] if isinstance(d, dict) else str(d)
            logger.info(f"Jinja2 template system initialized from {templates_path}")

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

        # Generate safe filename from title
        title = metadata.get('title', 'untitled')
        safe_filename = self._make_safe_filename(title)

        latex_path = output_dir / f"{safe_filename}.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        results["latex"] = str(latex_path)

        # Compile to PDF (uses tex filename stem for output)
        pdf_path = compile_tex_to_pdf(latex_path, output_dir)
        if pdf_path:
            results["pdf"] = pdf_path

        # Save JSON metadata with safe filename (after successful PDF generation)
        json_path = output_dir / f"{safe_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        results["json"] = str(json_path)
        logger.info(f"✅ Saved metadata to {json_path}")

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

    def _make_safe_filename(self, title: str, max_length: int = 100) -> str:
        """
        Create a safe filename from a title.

        Args:
            title: The book title
            max_length: Maximum filename length

        Returns:
            Safe filename string
        """
        import re

        # Remove special characters, keep alphanumeric, spaces, hyphens
        safe = re.sub(r'[^\w\s-]', '', title)
        # Replace spaces with underscores
        safe = re.sub(r'\s+', '_', safe)
        # Collapse multiple underscores
        safe = re.sub(r'_+', '_', safe)
        # Limit length
        safe = safe[:max_length]
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        # Fallback if empty
        if not safe:
            safe = "untitled"
        return safe

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
        logger.info(f"🔍 DEBUG _generate_latex: metadata keys: {list(metadata.keys())}")
        logger.info(f"🔍 DEBUG _generate_latex: '_pipeline_content' in metadata: {'_pipeline_content' in metadata}")

        pipeline_content = metadata.get("_pipeline_content", {})
        has_pipeline_content = bool(pipeline_content)

        logger.info(f"🔍 DEBUG _generate_latex: pipeline_content keys: {list(pipeline_content.keys()) if pipeline_content else 'None'}")
        logger.info(f"🔍 DEBUG _generate_latex: has_pipeline_content: {has_pipeline_content}")

        if has_pipeline_content:
            logger.info("✅ Including AI-generated content from pipeline in LaTeX document")
            if 'front_matter' in pipeline_content:
                logger.info(f"✅ DEBUG: Front matter sections: {list(pipeline_content['front_matter'].keys())}")
            if 'back_matter' in pipeline_content:
                logger.info(f"✅ DEBUG: Back matter sections: {list(pipeline_content['back_matter'].keys())}")
        else:
            logger.warning("⚠️ DEBUG: NO pipeline_content found - generating minimal LaTeX template")

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

        # Copyright page must always be on page ii (verso after title page i)
        copyright_content = f"""\\clearpage
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

        # --- Table of Contents - must start on odd page (recto) ---
        toc_content = """\\cleardoublepage
\\thispagestyle{{empty}}
\\tableofcontents*
\\cleardoublepage"""

        # --- Build Front Matter Sections ---
        front_matter_sections = ""
        if has_pipeline_content:
            front_matter_data = pipeline_content.get("front_matter", {})

            # Motivation - pass raw parsed_content for template detection
            if "motivation" in front_matter_data:
                raw_content = front_matter_data["motivation"]
                # Extract the actual dict if it's nested in parsed_content
                if isinstance(raw_content, dict) and 'publishers_note' in raw_content:
                    content_to_format = raw_content['publishers_note']
                else:
                    content_to_format = self._extract_content(raw_content)
                if content_to_format:
                    # Apply signature formatting before section formatting
                    content_to_format = self._format_publishers_note_signature(content_to_format)
                    front_matter_sections += self._format_section(
                        "Motivation",
                        content_to_format,
                        use_markdown=True
                    )

            # Historical Context - pass raw for template detection
            if "historical_context" in front_matter_data:
                raw_content = front_matter_data["historical_context"]
                # Extract the actual nested dict if present
                if isinstance(raw_content, dict) and 'historical_context' in raw_content:
                    content_to_format = raw_content['historical_context']
                else:
                    content_to_format = self._extract_content(raw_content)
                if content_to_format:
                    front_matter_sections += self._format_section(
                        "Historical Context",
                        content_to_format,
                        use_markdown=True
                    )

            # Abstracts - markdown string content
            if "abstracts_x4" in front_matter_data:
                abstracts_content = self._extract_content(front_matter_data["abstracts_x4"])
                if abstracts_content:
                    front_matter_sections += self._format_section(
                        "Abstracts",
                        abstracts_content,
                        use_markdown=True
                    )

            # Important Passages - markdown string content with special formatting
            if "important_passages" in front_matter_data:
                passages_content = self._extract_content(front_matter_data["important_passages"])
                if passages_content:
                    # First apply structural fixes (line breaks)
                    passages_content = self._format_passages_structure(passages_content)
                    # Convert markdown to LaTeX
                    passages_latex = markdown_to_latex(passages_content, skip_first_heading_if_matches="Important Passages")
                    # Then convert blockquotes to italic quote environments (post-conversion)
                    passages_latex = self._format_passages_quotes_latex(passages_latex)
                    front_matter_sections += self._format_section(
                        "Important Passages",
                        passages_latex,
                        use_markdown=False  # Already converted
                    )

        # --- Back Matter Intro Page ---
        back_matter_intro = """\\backmatter
\\chapter*{Back Matter}
\\addcontentsline{toc}{chapter}{Back Matter}

This section contains supplementary materials including indices to help readers navigate the document.

\\section*{Information}

Indexes are generated with reference to the current document's pagination, not the original.

\\cleardoublepage

% Custom footer for back matter with "Back Matter - N" format
\\makeoddfoot{mypagestyle}{}{Back Matter~-~}{\\thepage}
\\makeevenfoot{mypagestyle}{\\thepage}{Back Matter~-~}{}
"""

        # --- Build Back Matter Sections ---
        back_matter_sections = ""
        if has_pipeline_content:
            back_matter_data = pipeline_content.get("back_matter", {})

            # Index of Persons - markdown that needs conversion to LaTeX - ONLY include if non-empty
            if "index_persons" in back_matter_data:
                raw_content = back_matter_data["index_persons"]
                # Extract the actual content
                if isinstance(raw_content, dict) and 'index_of_persons' in raw_content:
                    persons_content = raw_content['index_of_persons']
                else:
                    persons_content = self._extract_content(raw_content)
                # Only add if content exists and is not empty/whitespace
                if persons_content and str(persons_content).strip():
                    # Check if content is substantive (not just error messages or placeholders)
                    content_str = str(persons_content).strip().lower()
                    if content_str and not content_str.startswith('no ') and not content_str.startswith('none'):
                        # Convert markdown to LaTeX using new converter
                        persons_content = convert_index_markdown_to_latex(persons_content)
                        back_matter_sections += self._format_section(
                            "Index of Persons",
                            persons_content,
                            use_markdown=False  # Already converted to LaTeX
                        )

            # Index of Places - markdown that needs conversion to LaTeX - ONLY include if non-empty
            if "index_places" in back_matter_data:
                raw_content = back_matter_data["index_places"]
                # Extract the actual content (could be list or string)
                if isinstance(raw_content, dict) and 'index_of_places' in raw_content:
                    places_content = raw_content['index_of_places']
                else:
                    places_content = self._extract_content(raw_content)
                # Only add if content exists and is not empty/whitespace
                if places_content and str(places_content).strip():
                    # Check if content is substantive (not just error messages or placeholders)
                    content_str = str(places_content).strip().lower()
                    if content_str and not content_str.startswith('no ') and not content_str.startswith('none'):
                        # Convert markdown to LaTeX using new converter
                        places_content = convert_index_markdown_to_latex(places_content)
                        back_matter_sections += self._format_section(
                            "Index of Places",
                            places_content,
                            use_markdown=False  # Already converted to LaTeX
                        )

            # Mnemonics (markdown that needs conversion to LaTeX) - at end of back matter
            if "mnemonics" in back_matter_data:
                logger.info("🔍 DEBUG: Found mnemonics in back_matter_data, extracting...")
                mnemonics_markdown = self._extract_content(back_matter_data["mnemonics"])
                logger.info(f"🔍 DEBUG: Extracted mnemonics markdown: {len(mnemonics_markdown)} chars")
                if mnemonics_markdown:
                    # Convert markdown to LaTeX using new converter
                    mnemonics_content = convert_mnemonics_markdown_to_latex(mnemonics_markdown)
                    logger.info(f"✅ DEBUG: Converted mnemonics to LaTeX: {len(mnemonics_content)} chars")

                    back_matter_sections += f"\n{mnemonics_content}\n"
                    logger.info("✅ DEBUG: Added formatted mnemonics to back_matter_sections")
                else:
                    logger.warning("⚠️  DEBUG: mnemonics_markdown was empty after extraction")
            else:
                logger.warning("⚠️  DEBUG: 'mnemonics' not found in back_matter_data")

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
\\usepackage[bookmarks=true,bookmarksopen=true,bookmarksnumbered=false,hidelinks]{{hyperref}}

% --- Page Style Setup ---
\\makepagestyle{{mypagestyle}}
\\makeoddhead{{mypagestyle}}{{}}{{}}{{\\small\\textit{{{title}}}}}
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

% --- Copyright page (ii - verso) - unnumbered ---
{copyright_content}

% --- Table of Contents (iii - recto) - unnumbered ---
{toc_content}

% --- Start roman numerals at page v (recto) for front matter ---
\\pagenumbering{{roman}}
\\setcounter{{page}}{{5}}
\\pagestyle{{mypagestyle}}

{front_matter_sections}

% --- Main matter - switch to arabic numerals with BODY:N format ---
\\mainmatter
\\pagenumbering{{arabic}}
\\setcounter{{page}}{{1}}

% Custom footer for body with "BODY:N" format in outside slot
\\makeoddfoot{{mypagestyle}}{{}}{{}}{{BODY:\\thepage}}
\\makeevenfoot{{mypagestyle}}{{BODY:\\thepage}}{{}}{{}}

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
            section_data: Section data from pipeline (either parsed_content dict directly,
                         a dict with 'content' key, or a plain string)

        Returns:
            Extracted content string, or empty string if extraction fails
        """
        if not section_data:
            return ""

        # CRITICAL FIX: Handle plain string content (markdown from text-formatted LLM responses)
        if isinstance(section_data, str):
            return section_data

        # Handle case where section_data is the parsed_content dict directly
        # (which has keys like 'keywords', 'publishers_note', 'historical_context', etc.)
        if "content" not in section_data:
            # Check if it's a dict with error
            if isinstance(section_data, dict) and "error" in section_data:
                logger.warning(f"Skipping section with error: {section_data.get('error', 'Unknown error')}")
                return ""

            # Try common content keys used in parsed_content responses
            content_keys_to_try = [
                "keywords", "publishers_note", "historical_context", "abstracts_x4",
                "important_passages", "index_of_persons", "index_of_places",
                "passages", "persons", "places", "mnemonics", "text", "content", "motivation", "context"
            ]
            for key in content_keys_to_try:
                if key in section_data:
                    return str(section_data[key])

            # If no specific key found, return the whole dict as string (will be ugly but visible)
            logger.warning(f"No recognized content key in section_data, available keys: {list(section_data.keys())}")
            return str(section_data)

        # Original logic: section_data has a 'content' key
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
            section_data: Section data from pipeline (either parsed_content dict directly,
                         or a dict with 'content' key)

        Returns:
            LaTeX content string, or empty string if extraction fails
        """
        if not section_data:
            return ""

        # Handle case where section_data is the parsed_content dict directly
        if "content" not in section_data:
            # Check for errors
            if isinstance(section_data, dict):
                if "error" in section_data:
                    logger.warning(f"Skipping mnemonics with error: {section_data.get('error', 'Unknown error')}")
                    return ""
                # Extract mnemonics_tex field directly from parsed_content
                if "mnemonics_tex" in section_data:
                    tex_content = section_data["mnemonics_tex"]
                    # Remove leading comment that might interfere with LaTeX compilation
                    # The LLM might generate: "% Comment text \\chapter*{Mnemonics}..."
                    # We need to remove just the "% Comment text " part
                    tex_content = tex_content.strip()
                    if tex_content.startswith('%'):
                        # Find the first backslash (start of LaTeX command) after the %
                        idx = tex_content.find('\\')
                        if idx > 0:
                            tex_content = tex_content[idx:]
                    return tex_content
                # If doesn't have mnemonics_tex, it's an error
                logger.warning(f"Mnemonics section_data missing 'mnemonics_tex' field: {list(section_data.keys())}")
                return ""
            return ""

        # Original logic: section_data has a 'content' key
        content = section_data["content"]

        # Check for errors
        if isinstance(content, dict):
            if "error" in content:
                logger.warning(f"Skipping mnemonics with error: {content.get('error', 'Unknown error')}")
                return ""
            # Extract mnemonics_tex field
            if "mnemonics_tex" in content:
                tex_content = content["mnemonics_tex"]
                # Remove leading comment
                tex_content = tex_content.strip()
                if tex_content.startswith('%'):
                    idx = tex_content.find('\\')
                    if idx > 0:
                        tex_content = tex_content[idx:]
                return tex_content
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
                        tex_content = content_json["mnemonics_tex"]
                        # Remove leading comment
                        tex_content = tex_content.strip()
                        if tex_content.startswith('%'):
                            idx = tex_content.find('\\')
                            if idx > 0:
                                tex_content = tex_content[idx:]
                        return tex_content
            except json.JSONDecodeError:
                # Not JSON, return as-is (might already be LaTeX)
                pass

        return str(content)

    def _collapse_page_ranges(self, page_refs: str) -> str:
        """Collapse consecutive page numbers into ranges (e.g., '1, 2, 3' -> '1-3')"""
        import re

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

    def _format_publishers_note_signature(self, content: str) -> str:
        """
        Format the publisher's note signature block to be flush right with empty line before.

        Args:
            content: Publisher's note markdown content

        Returns:
            Content with formatted signature
        """
        import re

        # Pattern: em-dash followed by name, location (typical signature format)
        # Example: "—Zero, Ann Arbor" or "— Zero, Ann Arbor"
        # We want to add empty line before and flush right

        def format_signature(match):
            # Get the signature line
            sig_line = match.group(0).strip()
            # Return with empty line before and flush right LaTeX command
            return f"\n\n\\begin{{flushright}}\n{sig_line}\n\\end{{flushright}}"

        # Match signature line (em-dash followed by text, possibly with comma)
        content = re.sub(
            r'\n\s*[—–-]\s*([A-Za-z\s]+,\s*[A-Za-z\s]+)\s*$',
            format_signature,
            content,
            flags=re.MULTILINE
        )

        return content

    def _format_passages_structure(self, content: str) -> str:
        """
        Fix structural formatting issues in Important Passages (line breaks).

        Args:
            content: Markdown content with passages

        Returns:
            Content with proper line breaks
        """
        import re

        # Fix LLM quirk: everything running together on one line
        # Insert newlines before key labels to create proper structure
        content = re.sub(r'(?<!\n)(Passage Topic:)', r'\n\n\1', content)
        content = re.sub(r'(?<!\n)(Location:)', r'\n\n\1', content)
        content = re.sub(r'(?<!\n)(Significance:)', r'\n\n\1', content)

        # Insert newline before blockquote if it follows Location on same line
        content = re.sub(r'(Location: BODY:\d+)\s+(>)', r'\1\n\n\2', content)

        # Insert newline before Significance if it follows blockquote text
        content = re.sub(r'(\.)(\s+)(Significance:)', r'\1\n\n\3', content)

        # Clean up multiple blank lines (3+ newlines become 2 newlines)
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def _format_passages_quotes_latex(self, latex_content: str) -> str:
        r"""
        Convert quote blocks in Important Passages to italic after LaTeX conversion.
        Also adds \par to label lines for proper paragraph closure.

        Args:
            latex_content: LaTeX content after markdown conversion

        Returns:
            LaTeX with italic quote blocks and proper paragraph breaks
        """
        import re

        # Find quote environments and add italic formatting
        latex_content = re.sub(
            r'\\begin\{quote\}(.*?)\\end\{quote\}',
            r'\\begin{quote}\\textit{\1}\\end{quote}',
            latex_content,
            flags=re.DOTALL
        )

        # Add \noindent and \par to label lines for flush left alignment and proper paragraph closure
        # This prevents hanging indent or parindent from bleeding through
        latex_content = re.sub(r'^(Passage Topic:.*?)$', r'\\noindent \1\\par', latex_content, flags=re.MULTILINE)
        latex_content = re.sub(r'^(Location:.*?)$', r'\\noindent \1\\par', latex_content, flags=re.MULTILINE)
        latex_content = re.sub(r'^(Significance:)$', r'\\noindent \1', latex_content, flags=re.MULTILINE)

        # Add blank line before subsequent "Passage Topic:" entries (not the first one)
        # Simple approach: add vspace before each noindent Passage Topic except at start
        lines = latex_content.split('\n')
        result_lines = []
        first_passage = True

        for i, line in enumerate(lines):
            if line.strip().startswith('\\noindent Passage Topic:') or line.strip().startswith('\\noindentPassage Topic:'):
                if not first_passage:
                    # Add spacing before this passage (but not the first one)
                    result_lines.append('\\vspace{12pt}')
                first_passage = False
            result_lines.append(line)

        return '\n'.join(result_lines)

    def _format_passages_quotes(self, content: str) -> str:
        """
        Format quoted text in Important Passages section.

        New format uses blockquotes (>) for passages, which will be rendered as italic
        blockquotes in LaTeX.

        Args:
            content: Markdown content with passages

        Returns:
            Content with formatted quotes
        """
        import re

        # Fix LLM quirk: everything running together on one line
        # Insert newlines before key labels to create proper structure
        content = re.sub(r'(?<!\n)(Passage Topic:)', r'\n\n\1', content)
        content = re.sub(r'(?<!\n)(Location:)', r'\n\n\1', content)
        content = re.sub(r'(?<!\n)(Significance:)', r'\n\n\1', content)

        # Insert newline before blockquote if it follows Location on same line
        content = re.sub(r'(Location: BODY:\d+)\s+(>)', r'\1\n\n\2', content)

        # Insert newline before Significance if it follows blockquote text
        content = re.sub(r'(\.)(\s+)(Significance:)', r'\1\n\n\3', content)

        # Clean up multiple blank lines (3+ newlines become 2 newlines)
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Convert blockquoted text to LaTeX quote environment with italics
        # Pattern: > followed by text (possibly multiline)
        def convert_blockquote_to_latex(match):
            quote_text = match.group(1).strip()

            # Remove any existing italic markers to avoid double-italics
            quote_text = re.sub(r'\*([^*]+?)\*', r'\1', quote_text)

            # Remove bullets if any (common LLM quirk)
            quote_text = re.sub(r'^\s*[•\-]\s+', '', quote_text)

            # Return LaTeX quote environment with italics
            return f"\\begin{{quote}}\\textit{{{quote_text}}}\\end{{quote}}"

        # Match blockquote sections (> marker followed by text)
        # Handle both single-line and multi-line blockquotes
        content = re.sub(
            r'^>\s*(.+?)(?=\n\n[A-Z]|\n\nSignificance:|\Z)',
            convert_blockquote_to_latex,
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        return content

    def _preprocess_markdown(self, content: str) -> str:
        """
        Preprocess markdown to fix common LLM-generated formatting issues.

        Args:
            content: Markdown content

        Returns:
            Preprocessed markdown
        """
        import re

        # Fix LLM responses that smash headings and body text together on one line
        # Pattern: ### Heading Text (capital letter starting new sentence)
        # Solution: Insert \n\n before headings and after headings

        # First, ensure headings are on their own lines (add newlines before ###)
        content = re.sub(r'([^\n])(#{1,6}\s+)', r'\1\n\n\2', content)

        # Second, split heading text from body text
        # Look for: "### Heading Words" followed by sentence-starting words
        # Common sentence starters: This, The, With, In, etc.
        content = re.sub(
            r'(#{1,6}\s+[^\n]+?)\s+((?:This|The|With|In|A|An|By|For|After|During|Following|Before|It)\s)',
            r'\1\n\n\2',
            content
        )

        # Fix LLM quirk: bold/italic/emoji within bullets
        # E.g., "• ** Economic analysis**" -> "• Economic analysis"
        # Remove formatting markers from bullet items
        content = re.sub(r'^(\s*[-*•]\s+)\*\*\s*(.+?)\s*\*\*', r'\1\2', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*[-*•]\s+)\*\s*(.+?)\s*\*', r'\1\2', content, flags=re.MULTILINE)
        # Remove emoji from bullets (common LLM quirk)
        content = re.sub(r'^(\s*[-*•]\s+)[🔍📊💡✨🎯]+\s*', r'\1', content, flags=re.MULTILINE)

        # Fix missing spaces after bold/italic markers followed by capital letter
        # E.g., "**Context**This document" -> "**Context** This document"
        content = re.sub(r'\*\*([A-Z])', r'** \1', content)
        content = re.sub(r'\*([A-Z])', r'* \1', content)

        # Fix missing spaces after sections/headings followed by capital letter
        # E.g., "SituationThis document" -> "Situation This document"
        content = re.sub(r'([a-z])([A-Z][a-z]+\s[A-Z])', r'\1 \2', content)

        # Insert newline before ## (but not before escaped \##)
        content = re.sub(r'(?<!\\)(\s+)(#{2,})\s+', r'\n\n\2 ', content)

        # Insert newline before lists if inline
        content = re.sub(r'(\S)(\s+)([-*])\s+', r'\1\n\n\3 ', content)

        # Convert markdown blockquotes (>) to proper format for pandoc
        # Ensure blockquotes have proper newlines
        lines = content.split('\n')
        processed_lines = []
        in_blockquote = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('>'):
                if not in_blockquote:
                    # Add blank line before blockquote if not already there
                    if processed_lines and processed_lines[-1].strip():
                        processed_lines.append('')
                    in_blockquote = True
                processed_lines.append(line)
            else:
                if in_blockquote and stripped:
                    # Add blank line after blockquote
                    processed_lines.append('')
                    in_blockquote = False
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _markdown_to_latex_skip_first(self, content: str, title: str) -> str:
        """
        Convert markdown to LaTeX, optionally skipping first heading if it matches title.

        Args:
            content: Markdown content
            title: Section title to match against first heading

        Returns:
            LaTeX content
        """
        return markdown_to_latex(content, skip_first_heading_if_matches=title)

    def _detect_content_type(self, content: Any) -> str:
        """
        Detect the type of content structure for template selection.

        Args:
            content: Content to analyze

        Returns:
            Content type identifier: 'dict_with_title', 'nested_dict', 'list', 'markdown', 'latex', or 'unknown'
        """
        if not content:
            return 'unknown'

        if isinstance(content, dict):
            # Check for title/content structure
            if 'title' in content and 'content' in content:
                return 'dict_with_title'
            # Check for nested dict (multiple keys with dict values)
            if len(content) > 1 and any(isinstance(v, dict) for v in content.values()):
                return 'nested_dict'
            # Single-key dict is likely markdown content
            return 'markdown'
        elif isinstance(content, list):
            return 'list'
        elif isinstance(content, str):
            # Try to detect if it's LaTeX or markdown
            if content.strip().startswith('\\chapter') or content.strip().startswith('\\section'):
                return 'latex'
            return 'markdown'

        return 'unknown'

    def _render_with_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render content using a Jinja2 template.

        Args:
            template_name: Name of the template file (e.g., 'section_markdown.tex.j2')
            context: Template context variables

        Returns:
            Rendered LaTeX content, or empty string if template not found
        """
        if not self.jinja_env:
            logger.warning("Jinja2 environment not initialized, cannot use templates")
            return ""

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            logger.warning(f"Template not found: {template_name}")
            return ""
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}", exc_info=True)
            return ""

    def _format_section(self, title: str, content: Any, use_markdown: bool = True) -> str:
        """
        Format a section with title and content for LaTeX inclusion.
        Uses Jinja2 templates if available, falls back to legacy method.

        Args:
            title: Section title
            content: Section content (can be str, dict, or list)
            use_markdown: If True, convert markdown to LaTeX

        Returns:
            Formatted LaTeX section
        """
        # Check if content is empty
        if not content:
            return ""
        if isinstance(content, str) and not content.strip():
            return ""

        # Try template-based rendering first
        if self.jinja_env:
            content_type = self._detect_content_type(content)
            logger.info(f"Formatting section '{title}' with detected type: {content_type}")

            # Select appropriate template based on content type
            template_name = None
            context = {'title': title, 'content': content}

            if content_type == 'dict_with_title':
                # Content is a dict with title and content keys
                template_name = 'section_with_title.tex.j2'
                if isinstance(content, dict):
                    context['title'] = content.get('title', title)
                    context['content'] = content.get('content', '')
            elif content_type == 'nested_dict':
                # Complex nested structure
                template_name = 'nested_dict.tex.j2'
            elif content_type == 'list':
                # List of items (e.g., indices)
                template_name = 'index_list.tex.j2'
                context['items'] = content
            elif content_type == 'latex':
                # Pre-formatted LaTeX
                template_name = 'section_latex.tex.j2'
            elif content_type == 'markdown':
                # Plain markdown string
                template_name = 'section_markdown.tex.j2'
                # Extract actual markdown if it's wrapped in a dict
                if isinstance(content, dict):
                    # Try common keys
                    for key in ['text', 'content', 'markdown']:
                        if key in content:
                            context['content'] = content[key]
                            break
                    else:
                        # Use first value if no recognized key
                        context['content'] = list(content.values())[0] if content else ''

            if template_name:
                rendered = self._render_with_template(template_name, context)
                if rendered:
                    logger.info(f"Successfully rendered section '{title}' using template {template_name}")
                    return rendered
                else:
                    logger.warning(f"Template rendering failed for '{title}', falling back to legacy method")

        # Legacy fallback method
        escaped_title = escape_latex(title)

        # Convert content to string if needed
        if not isinstance(content, str):
            content = str(content)

        # Convert content if needed
        if use_markdown:
            # Preprocess markdown
            content = self._preprocess_markdown(content)
            # Skip first heading if it matches the chapter title
            latex_content = markdown_to_latex(content, skip_first_heading_if_matches=title)
        else:
            latex_content = content

        # Ensure chapter starts on recto (odd) page
        # Don't add cleardoublepage at end to avoid creating extra blank pages
        return f"""\\cleardoublepage
\\pdfbookmark[0]{{{escaped_title}}}{{sec:{escaped_title.replace(' ', '_')}}}
\\chapter*{{{escaped_title}}}
\\addcontentsline{{toc}}{{chapter}}{{{escaped_title}}}

{latex_content}
"""

    def _generate_cover(self, metadata: Dict[str, Any], output_dir: Path) -> Optional[str]:
        """Generate cover using imprint template."""
        try:
            cover_template = self.template_dir / "cover_template.tex"
            if cover_template.exists():
                # create_cover_latex expects: json_path, output_dir, template_path, build_dir, replacements, debug_mode, data
                # We're passing metadata directly as data parameter
                replacements = {
                    "title": metadata.get("title", "Untitled"),
                    "author": metadata.get("author", "Unknown Author"),
                    "subtitle": metadata.get("subtitle", ""),
                    "imprint": metadata.get("imprint", "Nimble Ultra Global")
                }
                return create_cover_latex(
                    json_path=None,  # Not using JSON file
                    output_dir=Path(output_dir),
                    template_path=Path(cover_template),
                    build_dir=Path(output_dir),  # Use output_dir as build_dir
                    replacements=replacements,
                    debug_mode=False,
                    data=metadata  # Pass metadata directly
                )
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

    # Expand ~ in path if present
    if body_source:
        body_source = Path(body_source).expanduser()

    if body_source and Path(body_source).exists():
        logger.info(f"📄 Processing with body source: {body_source}")

        # Transform LLM responses into _pipeline_content structure for prepress
        logger.info(f"🔍 DEBUG: Checking for content in data. Keys in data: {list(data.keys())}")

        try:
            logger.info("🔍 DEBUG: Starting _pipeline_content transformation")
            # Build _pipeline_content from either top-level fields (new) or responses array (legacy)
            pipeline_content = {"front_matter": {}, "back_matter": {}}

            # PREFERRED METHOD: Check for top-level markdown fields first (new behavior after llm_get_book_data.py fixes)
            # This allows us to use markdown content directly without parsing responses
            top_level_front_matter = {
                'bibliographic_key_phrases': 'keywords',  # Map to actual top-level key
                'motivation': 'motivation',
                'historical_context': 'historical_context',
                'abstracts_x4': 'abstracts_x4',
                'important_passages': 'most_important_passages_with_reasoning'
            }

            top_level_back_matter = {
                'index_persons': 'index_of_persons',
                'index_places': 'index_of_places',
                'mnemonics': 'mnemonics'
            }

            # Check if we have top-level fields with content
            has_top_level_content = False
            for mapped_key, json_key in top_level_back_matter.items():
                if json_key in data and data[json_key]:
                    pipeline_content['back_matter'][mapped_key] = data[json_key]
                    logger.info(f"✅ DEBUG: Using top-level field '{json_key}' for back_matter[{mapped_key}]")
                    has_top_level_content = True

            for mapped_key, json_key in top_level_front_matter.items():
                if json_key in data and data[json_key]:
                    pipeline_content['front_matter'][mapped_key] = data[json_key]
                    logger.info(f"✅ DEBUG: Using top-level field '{json_key}' for front_matter[{mapped_key}]")
                    has_top_level_content = True

            # FALLBACK METHOD: Use responses array if top-level fields not found (backward compatibility)
            if not has_top_level_content and 'responses' in data:
                logger.info("🔍 DEBUG: No top-level content found, falling back to responses array")

                # Find the response list (may be under model name key)
                responses_data = data['responses']
                logger.info(f"🔍 DEBUG: responses_data type: {type(responses_data)}")

                if isinstance(responses_data, dict):
                    # Get the first model's responses
                    model_key = list(responses_data.keys())[0]
                    responses_list = responses_data[model_key]
                    logger.info(f"🔍 DEBUG: Found model key: {model_key}, responses count: {len(responses_list)}")
                else:
                    responses_list = responses_data
                    logger.info(f"🔍 DEBUG: Direct responses list, count: {len(responses_list)}")

                # Map prompt keys to front/back matter sections with name transformations
                front_matter_mappings = {
                    'bibliographic_key_phrases': 'bibliographic_key_phrases',
                    'gemini_get_basic_info_from_public_domain': 'basic_info',
                    'motivation': 'motivation',
                    'place_in_historical_context': 'historical_context',
                    'abstracts_x4': 'abstracts_x4',
                    'most_important_passages_with_reasoning': 'important_passages'
                }

                back_matter_mappings = {
                    'index_of_persons': 'index_persons',
                    'index_of_places': 'index_places',
                    'mnemonics_prompt': 'mnemonics'
                }

                # Organize responses into front/back matter
                for i, response in enumerate(responses_list):
                    prompt_key = response.get('prompt_key', '')
                    parsed_content = response.get('parsed_content', {})
                    logger.info(f"🔍 DEBUG: Response {i+1}: prompt_key={prompt_key}, has parsed_content={bool(parsed_content)}")

                    if prompt_key in front_matter_mappings:
                        # Map to expected key name for template
                        mapped_key = front_matter_mappings[prompt_key]
                        pipeline_content['front_matter'][mapped_key] = parsed_content
                        logger.info(f"✅ DEBUG: Added to front_matter[{mapped_key}] from responses")
                    elif prompt_key in back_matter_mappings:
                        # Map to expected key name for template
                        mapped_key = back_matter_mappings[prompt_key]
                        pipeline_content['back_matter'][mapped_key] = parsed_content
                        logger.info(f"✅ DEBUG: Added to back_matter[{mapped_key}] from responses")
                    else:
                        logger.warning(f"⚠️ DEBUG: prompt_key '{prompt_key}' not mapped")

            # Add to data
            data['_pipeline_content'] = pipeline_content
            logger.info(f"✅ Built _pipeline_content with {len(pipeline_content['front_matter'])} front matter and {len(pipeline_content['back_matter'])} back matter sections")
            logger.info(f"🔍 DEBUG: Front matter keys: {list(pipeline_content['front_matter'].keys())}")
            logger.info(f"🔍 DEBUG: Back matter keys: {list(pipeline_content['back_matter'].keys())}")

        except Exception as e:
            logger.error(f"❌ DEBUG: Exception building _pipeline_content: {e}", exc_info=True)

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
